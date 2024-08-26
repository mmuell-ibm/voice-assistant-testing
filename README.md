## Build and Run Image
podman build --platform linux/amd64 -t assistant-voice-image . 

podman run --platform linux/amd64 -it --rm -p 8080:8080 assistant-voice-image
