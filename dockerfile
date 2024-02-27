# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of your application's source code into the container
COPY . /app/

# Define environment variables (optional)
ENV MONGO_URL="mongodb://localhost:27017/"
ENV DISCORD_TOKEN="your discord token goes here"

# Run your application
CMD ["python", "main.py"]
