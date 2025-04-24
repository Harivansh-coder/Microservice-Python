# This is a Flask application that uses the microservice architecture to convert mp4 files to mp3 files.

### The application is divided into following microservices:

- **Authentication Service**: This service is responsible for user authentication and authorization. It uses JWT tokens for secure communication between the client and server.
- **Gateway Service**: This service acts as a reverse proxy and routes requests to the appropriate microservice. It also handles load balancing and caching.
- **File Upload Service**: This service is responsible for uploading files to the server. It uses Flask-Uploads to handle file uploads and stores the files in a local directory.
- **File Conversion Service**: This service is responsible for converting mp4 files to mp3 files. It uses the moviepy library to perform the conversion.
- **File Download Service**: This service is responsible for downloading the converted mp3 files. It uses Flask-Uploads to handle file downloads and serves the files from a local directory.
- **Notiofication Service**: This service is responsible for sending notifications to the user when the file conversion is complete. It uses RabbitMQ to send messages between the microservices.

### The application is built using the following technologies:

- **Flask**: A lightweight web framework for Python that is used to build the microservices.
- **Marshmallow**: A library for object serialization and deserialization that is used to convert Python objects to JSON and vice versa.
- **PostgreSQL**: A relational database management system that is used to store user data for authentication and authorization.
- **RabbitMQ**: A message broker that is used to handle communication between the microservices. It is used to send messages between the File Upload Service and the File Conversion Service.
- **MongoDB**: A NoSQL database that is used to store the mp4 files and mp3 files using GridFS.
- **Docker**: A platform that is used to create, deploy, and run applications in containers. It is used to containerize the microservices and run
  them in isolated environments.
- Kubernetes: An open-source container orchestration platform that is used to automate the deployment, scaling, and management of containerized applications. It is used to manage the microservices and ensure high availability and scalability.

### Architecture Diagram

- The auth and gateway services communicate in strong consistency with each other.
- The gateway service communicates with the file upload service and file conversion service in eventual consistency.
- The file upload service communicates with the file conversion service in eventual consistency using RabbitMQ.
