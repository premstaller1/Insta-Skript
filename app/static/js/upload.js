document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file-input");
    const uploadButton = document.getElementById("upload-button");
    const mediaList = document.getElementById("media-list");
    const publishButton = document.getElementById("publish-button");
    const profileSelector = document.getElementById("profile");
    const feedback = document.getElementById("upload-feedback");

    let uploadedFiles = [];
    let childrenIds = [];  // Store the carousel item IDs returned from the backend

    // Upload button click event
    uploadButton.addEventListener("click", async () => {
        const files = fileInput.files;
        feedback.textContent = ""; // Clear previous feedback messages

        // Validate file selection
        if (files.length === 0) {
            feedback.textContent = "Please select files to upload.";
            feedback.className = "text-danger";
            return;
        }

        // Check total files including previously uploaded ones
        if (uploadedFiles.length + files.length > 10) {
            feedback.textContent = "You can upload a maximum of 10 media files.";
            feedback.className = "text-danger";
            return;
        }

        const formData = new FormData();
        formData.append("profile", profileSelector.value);  // Add profile to the form data

        // Validate individual files for type and size
        for (const file of files) {
            const isValidType = ["image/jpeg", "video/mp4"].includes(file.type);
            const isValidSize = file.size <= 15 * 1024 * 1024; // 15MB limit

            if (!isValidType) {
                feedback.textContent = `Unsupported file type: ${file.name}`;
                feedback.className = "text-danger";
                return;
            }
            if (!isValidSize) {
                feedback.textContent = `File size exceeds 15MB: ${file.name}`;
                feedback.className = "text-danger";
                return;
            }
            formData.append("file", file); // Add valid file to FormData
        }

        try {
            // Send files to the backend
            const response = await fetch("/publish_instagram/upload_carousel", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            if (result.success) {
                childrenIds = result.children_ids;  // Get carousel item IDs from the backend
                renderMediaList();  // Refresh the UI
                fileInput.value = "";  // Clear file input
                feedback.textContent = "Files uploaded successfully!";
                feedback.className = "text-success";
            } else {
                // Handle server response errors
                feedback.textContent = result.message || "Failed to upload files.";
                feedback.className = "text-danger";
            }
        } catch (error) {
            // Handle network or other errors
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

        if (childrenIds.length === 0) {
            alert("Please upload media before publishing.");
            return;
        }

        try {
            const response = await fetch("/publish_instagram/publish_carousel", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ caption, profile, children_ids: childrenIds }),  // Pass carousel item IDs
            });

            const result = await response.json();
            if (result.success) {
                alert("Carousel published successfully!");
                uploadedFiles = [];
                childrenIds = [];  // Clear the stored IDs
                renderMediaList();
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error("Error publishing media:", error);
            alert("An error occurred while publishing the carousel.");
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
            const response = await fetch("/publish_instagram/delete", {
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
