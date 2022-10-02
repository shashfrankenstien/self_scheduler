FROM alpine:latest

RUN apk update
RUN apk add python3 py3-pip make

WORKDIR /root/self_scheduler/

COPY . .
RUN python3 -m pip install --upgrade pip wheel
RUN python3 -m pip install --no-cache-dir -r requirements.txt


ENV ENV="/etc/profile"
RUN echo 'alias l="ls -all"' >> /etc/profile

CMD ["python3", "server.py"]


# sudo docker build -t selfsched .
# sudo docker run -itd --name ss -p 8000:5000 -v $(pwd)/projects:/etc/projects -e WORKSPACE_PATH='/etc/projects' selfsched
# sudo docker stop ss
# sudo docker system prune


# podman build -t selfsched .
# podman run -itd --name ss -p 8000:5000 -v $(pwd)/projects:/etc/projects -e WORKSPACE_PATH='/etc/projects' localhost/selfsched
# podman stop ss
# podman system prune


