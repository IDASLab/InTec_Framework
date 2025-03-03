
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip3 install pip --upgrade

RUN pip3 install cython numpy==1.23.4
RUN pip3 install --default-timeout=200 --no-cache-dir scikit-learn
RUN pip3 install --default-timeout=200 --no-cache-dir pandas 
RUN pip3 install --default-timeout=200 paho-mqtt==1.6.1

RUN apt-get remove -y g++ && rm -rf /var/lib/apt/lists/*
RUN pip3 install --default-timeout=200 tflite-runtime==2.13.0

# Copy application files
COPY . .

# Set environment variables (Corrected format)
ENV Name="sensor01"
ENV Subject="subject1"
ENV Broker="intec-emqx-broker"
ENV Topic="sensor/data"
ENV WindowSize="25"
ENV Rate="50"
ENV Time="60"

# Run the application
CMD ["python", "inference.py"]

