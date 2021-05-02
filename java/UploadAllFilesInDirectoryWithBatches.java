import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.FileVisitor;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * This script will upload all .csv and .csv.gz files from a directory as data into a specific data set
 * and create batches based on the directory structure.
 * Usage:
 * <pre>
 *   java UploadAllFilesInDirectoryWithBatches -i <InputDir> -d <DataSetId> -u <APIUserName> -p <APIIUserPassword>
 * </pre>
 * <p>
 * If you have a directory structure as follows:
 * </p>
 * <pre>
 *   root
 *     |_ subdir1
 *        |_ file1_1.csv
 *        |_ file1_2.csv
 *     |_ subdir2
 *        |_ file2_1.csv
 *     |_ file_without_batch.csv
 * </pre>
 * <p>
 *   The script will create 2 batches {@code subdir1} and {@code subdir2},
 *   and upload {@code file_without_batch.csv} in the default batch.
 * </p>
 * <p>
 * Note that the script requires at least JDK 11.
 * </p>
 */
class UploadAllFilesInDirectoryWithBatches {

  private static final String PLATFORM_URL = "https://api.platform-xyzt.ai";

  private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder().build();
  private static final String MULTI_PART_BOUNDARY = "-------------" + UUID.randomUUID().toString();

  public static void main(String[] args) throws IOException {
    try {
      uploadDirectory(new Arguments(args));
    } catch (IllegalArgumentException e) {
      printUsage();
    }
  }

  private static void uploadDirectory(Arguments arguments) throws IOException {
    Path root = Paths.get(arguments.inputDirectory);

    File[] filesAndDirectories = root.toFile().listFiles();
    if(filesAndDirectories == null){
      return;
    }
    for (File fileOrDirectory : filesAndDirectories) {
      if (fileOrDirectory.isFile()) {
        String fileName = fileOrDirectory.getName();
        if (!fileName.endsWith(".csv") || fileName.endsWith(".csv.gz")) {
          continue;
        }
        //Files under the root should be uploaded without batch
        try {
          System.out.println("Uploading file " + fileName + " without batch");
          uploadFile(fileOrDirectory.toPath(), null, arguments);
        } catch (InterruptedException e) {
          e.printStackTrace();
        }
      } else {
        String batch = fileOrDirectory.getName();
        Files.walkFileTree(fileOrDirectory.toPath(), new FileVisitor<Path>() {
          @Override
          public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs)
              throws IOException {
            return FileVisitResult.CONTINUE;
          }

          @Override
          public FileVisitResult visitFile(Path file, BasicFileAttributes attrs)
              throws IOException {
            String fileName = file.toFile().getName();
            if (fileName.endsWith(".csv") || fileName.endsWith(".csv.gz")) {
              System.out.println("Uploading file " + fileName + " to batch " + batch);
              try {
                uploadFile(file, batch, arguments);
              } catch (InterruptedException e) {
                e.printStackTrace();
              }
            }
            return FileVisitResult.CONTINUE;
          }

          @Override
          public FileVisitResult visitFileFailed(Path file, IOException exc) throws IOException {
            exc.printStackTrace();
            return FileVisitResult.CONTINUE;
          }

          @Override
          public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
            return FileVisitResult.CONTINUE;
          }
        });
      }
    }
  }

  private static void uploadFile(Path file, String batchNameOrNull, Arguments arguments)
      throws IOException, InterruptedException {
    String fileName = file.toFile().getName();
    String batchQueryParameter = batchNameOrNull != null ? "?batch=" + batchNameOrNull.replace(" ", "_") : "";
    HttpRequest uploadDataRequest = newAuthenticatedMultipartFormRequest(arguments)
        .uri(
            toAbsoluteURI(String.format("/datasets/%s/data/upload" + batchQueryParameter, arguments.dataSetId)))
        .POST(multipartFile(file, fileName.endsWith(".csv") ? "text/csv" : "application/gzip",
            "file"))
        .build();
    HttpResponse<String> response =
        HTTP_CLIENT.send(uploadDataRequest, HttpResponse.BodyHandlers.ofString());
    if (!(response.statusCode() >= 200 && response.statusCode() < 300)) {
      System.err.println(
          "Upload file " + fileName + " failed. Status code: " + response.statusCode() +
              ". Message: " + response.body());
    }
  }

  private static HttpRequest.BodyPublisher multipartFile(Path file,
                                                         String mediaType,
                                                         String propertyName) throws IOException {
    Map<String, byte[]> data = Map.of(propertyName, Files.readAllBytes(file));
    String fileName = file.toFile().getName();
    return HttpRequest.BodyPublishers
        .ofByteArrays(buildMultipartData(data, fileName, mediaType));
  }

  private static List<byte[]> buildMultipartData(Map<String, byte[]> data,
                                                 String filename,
                                                 String mediaType) {
    var byteArrays = new ArrayList<byte[]>();
    var separator = ("--" + MULTI_PART_BOUNDARY +
        "\r\nContent-Disposition: form-data; name=").getBytes(
        StandardCharsets.UTF_8);

    for (var entry : data.entrySet()) {
      byteArrays.add(separator);
      byteArrays.add(("\"" + entry.getKey() + "\"; filename=\"" + filename + "\"\r\nContent-Type:" +
          mediaType + "\r\n\r\n").getBytes(StandardCharsets.UTF_8));
      byteArrays.add(entry.getValue());
      byteArrays.add("\r\n".getBytes(StandardCharsets.UTF_8));
    }

    byteArrays.add(("--" + MULTI_PART_BOUNDARY + "--")
        .getBytes(StandardCharsets.UTF_8));
    return byteArrays;
  }

  private static HttpRequest.Builder newAuthenticatedMultipartFormRequest(
      Arguments arguments) throws IOException, InterruptedException {
    //As the JWT tokens are only valid for a limited time, and uploading a file can take a while
    //we'll fetch a new token for every request
    String jwtToken = getJWTToken(arguments);
    return HttpRequest.newBuilder()
        .header("Authorization", String.format("Bearer %s", jwtToken))
        .header("Content-type", "multipart/form-data; boundary=" + MULTI_PART_BOUNDARY)
        .header("Accept", "application/json");
  }

  private static HttpRequest.Builder newJSONRequestBuilder() {
    return HttpRequest.newBuilder()
        .header("Content-type", "application/json")
        .header("Accept", "application/json");
  }

  private static String getJWTToken(Arguments arguments) throws IOException, InterruptedException {
    String userName = arguments.userName;
    String password = arguments.password;
    //For more complex bodies, using a dedicated JSON library would be better
    String body = String.format("{\"userName\":\"%s\",\"password\":\"%s\"}", userName, password);
    HttpRequest loginRequest = newJSONRequestBuilder()
        .uri(toAbsoluteURI("/tokens"))
        .POST(HttpRequest.BodyPublishers.ofString(body))
        .build();

    HttpResponse<String> loginResponse =
        HTTP_CLIENT.send(loginRequest, HttpResponse.BodyHandlers.ofString());
    if (loginResponse.statusCode() >= 200 && loginResponse.statusCode() < 300) {
      //For more complex responses, using a dedicated JSON library would be better
      //The response looks like {"jwtToken":"<token>"}
      //We can split take the part after the :, strip away the " and the } and have the token
      String responseBody = loginResponse.body();
      return responseBody
          .substring(responseBody.indexOf(":" ) + 1) // Only retain the last part
          .replace("\"", "") // Get rid of the quotes
          .replace("}","") // Get rid of the closing }
          .trim(); // Get rid of any trailing whitespace
    }
    throw new RuntimeException(String
        .format("Could not obtain token. Status code [%d]: %s", loginResponse.statusCode(),
            loginResponse.body()));
  }

  private static URI toAbsoluteURI(String relativePath) {
    String baseUrl = PLATFORM_URL + "/" + "public/api";
    relativePath = relativePath.startsWith("/") ? relativePath : "/" + relativePath;
    return URI.create(baseUrl + relativePath);
  }

  private static void printUsage() {
    System.out.println(
        "Uploads all files from the specified directory into the specified data set, using the subdirectories as batches.\n" +
            "Usage: \n\n" +
            "java UploadAllFilesInDirectoryWithBatches -i <InputDir> -d <DataSetId> -u <APIUserName> -p <APIIUserPassword>"
    );
  }

  private static class Arguments {
    final String inputDirectory;
    final String dataSetId;
    final String userName;
    final String password;

    Arguments(String[] args) throws IllegalArgumentException {
      if (args.length != 8) {
        throw new IllegalArgumentException("Expected 8 arguments, got " + args.length);
      }
      try {
        inputDirectory = args[Arrays.asList(args).indexOf("-i") + 1];
        dataSetId = args[Arrays.asList(args).indexOf("-d") + 1];
        userName = args[Arrays.asList(args).indexOf("-u") + 1];
        password = args[Arrays.asList(args).indexOf("-p") + 1];
      } catch (RuntimeException e) {
        throw new IllegalArgumentException("Could not parse arguments");
      }
    }
  }
}
