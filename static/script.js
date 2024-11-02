document.addEventListener("DOMContentLoaded", () => {
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("file");
    const uploadButton = document.getElementById("uploadButton");
    const stopButton = document.getElementById("stopButton");
    const pauseButton = document.getElementById("pauseButton");
    const fileUploadStatus = document.getElementById("file-upload-status");

    // Trigger file input when clicking on the upload zone
    uploadZone.addEventListener("click", () => fileInput.click());

    // Update the file upload status message when a file is selected
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            fileUploadStatus.style.display = "block";
        }
    });

    // Handle drag-over and drop events for the upload zone
    uploadZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadZone.classList.add("dragging");
    });

    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("dragging");
    });

    uploadZone.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadZone.classList.remove("dragging");

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files; // triggers the "change" event above
            fileUploadStatus.style.display = "block";
        }
    });

    // Start upload when the Upload and Generate button is clicked
    uploadButton.onclick = function(event) {
        event.preventDefault();

        if (fileInput.files.length === 0) {
            alert("Please select a file to upload.");
            return;
        }

        document.getElementById("loading-spinner").style.display = "block";
        stopButton.style.display = "block";
        pauseButton.style.display = "block";

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        fetch("/upload_and_process", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const eventSource = new EventSource("/stream_process");

                eventSource.onmessage = function(event) {
                    const captionInfo = JSON.parse(event.data);

                    const projectCard = document.createElement("div");
                    projectCard.classList.add("card", "mt-4", "shadow", "rounded");
                    projectCard.id = `project-card-${captionInfo.project_name}`;

                    const cardBody = document.createElement("div");
                    cardBody.classList.add("card-body");

                    const title = document.createElement("h5");
                    title.classList.add("card-title");
                    title.textContent = captionInfo.project_name;

                    const captionText = document.createElement("textarea");
                    captionText.classList.add("form-control", "caption-text");
                    captionText.value = captionInfo.caption;
                    captionText.disabled = true;

                    const editButton = document.createElement("button");
                    editButton.classList.add("btn", "btn-secondary", "mt-3", "mr-2");
                    editButton.textContent = "✏️ Edit";
                    editButton.onclick = () => {
                        captionText.disabled = !captionText.disabled;
                        editButton.textContent = captionText.disabled ? "✏️ Edit" : "💾 Save";
                        if (captionText.disabled) {
                            fetch(`/update_caption`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    project_name: captionInfo.project_name,
                                    caption: captionText.value
                                })
                            });
                        }
                    };

                    const deleteButton = document.createElement("button");
                    deleteButton.classList.add("btn", "btn-danger", "mt-3", "mr-2");
                    deleteButton.textContent = "🗑️ Delete";
                    deleteButton.onclick = () => {
                        fetch(`/delete_project`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ project_name: captionInfo.project_name })
                        }).then(response => response.json())
                          .then(data => {
                            if (data.success) {
                                projectCard.remove();
                            }
                        });
                    };

                    const acceptButton = document.createElement("button");
                    acceptButton.classList.add("btn", "btn-success", "mt-3");
                    acceptButton.textContent = "✅ Accept";
                    acceptButton.onclick = () => {
                        fetch(`/accept_project`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ project_name: captionInfo.project_name })
                        }).then(response => response.json())
                          .then(data => {
                            if (data.success) {
                                alert("Project accepted and hidden from the app.");
                                projectCard.remove();  // Remove the project card from the UI
                            } else {
                                alert("Failed to accept the project.");
                            }
                        });
                    };

                    cardBody.appendChild(title);
                    cardBody.appendChild(captionText);
                    cardBody.appendChild(editButton);
                    cardBody.appendChild(deleteButton);
                    cardBody.appendChild(acceptButton);

                    const imageRow = document.createElement("div");
                    imageRow.classList.add("row", "mt-3");
                    captionInfo.images.forEach(imageUrl => {
                        const imageCol = document.createElement("div");
                        imageCol.classList.add("col-md-4");
                        const img = document.createElement("img");
                        img.src = imageUrl;
                        img.classList.add("img-fluid", "rounded");
                        imageCol.appendChild(img);
                        imageRow.appendChild(imageCol);
                    });

                    cardBody.appendChild(imageRow);
                    projectCard.appendChild(cardBody);
                    document.getElementById("captions-container").appendChild(projectCard);
                };

                stopButton.onclick = function() {
                    fetch("/stop_process", { method: "POST" })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                eventSource.close();
                                document.getElementById("loading-spinner").style.display = "none";
                                stopButton.style.display = "none";
                                pauseButton.style.display = "none";
                            }
                        });
                };

                pauseButton.onclick = function() {
                    fetch("/pause_process", { method: "POST" })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                pauseButton.textContent = data.paused ? "▶️ Resume Process" : "⏸ Pause Process";
                                document.getElementById("loading-spinner").querySelector("p").textContent = data.paused ? "Paused" : "Generating captions and downloading images, please wait...";
                            }
                        });
                };

                eventSource.onerror = function() {
                    eventSource.close();
                    document.getElementById("loading-spinner").style.display = "none";
                    stopButton.style.display = "none";
                    pauseButton.style.display = "none";
                };
            } else {
                alert("File upload failed.");
                document.getElementById("loading-spinner").style.display = "none";
            }
        })
        .catch(error => {
            console.error("Error:", error);
            document.getElementById("loading-spinner").style.display = "none";
        });
    };
});
