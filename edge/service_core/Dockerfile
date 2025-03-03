# Use official Node.js LTS image
FROM node:18

# Set working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose the configured port from .env
ARG HTTP_PORT
ENV PORT=$HTTP_PORT

# Expose port dynamically from .env
EXPOSE $PORT

# Start the application
CMD ["node", "server.js"]
