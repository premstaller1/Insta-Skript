document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file-input");
    const uploadButton = document.getElementById("upload-button");
    const mediaList = document.getElementById("media-list");
    const publishButton = document.getElementById("publish-button");
    const profileSelector = document.getElementById("profile");
    const feedback = document.getElementById("upload-feedback");

    let uploadedFiles = [];

    // Upload button click event
    uploadButton.addEventListener("click", async () => {
        const files = fileInput.files;
        feedback.textContent = ""; // Clear feedback

        if (files.length === 0) {
            feedback.textContent = "Please select files to upload.";
            feedback.className = "text-danger";
            return;
        }

        if (uploadedFiles.length + files.length > 10) {
            feedback.textContent = "You can upload a maximum of 10 media files.";
            feedback.className = "text-danger";
            return;
        }

        const formData = new FormData();
        for (const file of files) {
            if (!["image/jpeg", "video/mp4"].includes(file.type)) {
                feedback.textContent = `Unsupported file type: ${file.name}`;
                feedback.className = "text-danger";
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                feedback.textContent = `File size exceeds 5MB: ${file.name}`;
                feedback.className = "text-danger";
                return;
            }
            formData.append("file", file);
        }

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();
            if (result.success) {
                uploadedFiles = result.files;
                renderMediaList();
                fileInput.value = ""; // Clear file input
                feedback.textContent = "Files uploaded successfully!";
                feedback.className = "text-success";
            } else {
                feedback.textContent = result.message;
                feedback.className = "text-danger";
            }
        } catch (error) {
            console.error("Error uploading files:", error);
            feedback.textContent = "An error occurred while uploading files.";
            feedback.className = "text-danger";
        }
    });

    // Publish button click event
    publishButton.addEventListener("click", async () => {
        const caption = document.getElementById("caption").value;
        const profile = profileSelector.value;

        if (!profile) {
            alert("Please select a profile.");
            return;
        }

        if (uploadedFiles.length === 0) {
            alert("Please upload media before publishing.");
            return;
        }

        try {
            const response = await fetch("/publish", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ caption, profile }),
            });
            const result = await response.json();
            if (result.success) {
                alert(result.message);
                uploadedFiles = [];
                renderMediaList();
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error("Error publishing media:", error);
            alert("An error occurred while publishing media.");
        }
    });

    // Render uploaded media list
    function renderMediaList() {
        mediaList.innerHTML = "";
        uploadedFiles.forEach((file) => {
            const listItem = document.createElement("li");
            listItem.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");
            listItem.textContent = file.filename;

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Delete";
            deleteButton.classList.add("btn", "btn-danger", "btn-sm");
            deleteButton.addEventListener("click", () => deleteMedia(file.filename));

            listItem.appendChild(deleteButton);
            mediaList.appendChild(listItem);
        });
    }

    // Delete media function
    async function deleteMedia(filename) {
        try {
            const response = await fetch("/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename }),
            });

            const result = await response.json();
            if (result.success) {
                uploadedFiles = result.files;
                renderMediaList();
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error("Error deleting media:", error);
            alert("An error occurred while deleting media.");
        }
    }
});
