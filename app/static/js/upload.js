document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file-input");
    const uploadButton = document.getElementById("upload-button");
    const mediaList = document.getElementById("media-list");
    const publishButton = document.getElementById("publish-button");
    const profileSelector = document.getElementById("profile");

    let uploadedFiles = [];

    uploadButton.addEventListener("click", async () => {
        const files = fileInput.files;

        if (files.length === 0) {
            alert("Please select files to upload.");
            return;
        }

        if (uploadedFiles.length + files.length > 10) {
            alert("You can upload a maximum of 10 media files.");
            return;
        }

        const formData = new FormData();
        for (const file of files) {
            formData.append("file", file);
        }

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        if (result.success) {
            uploadedFiles = result.files;
            renderMediaList();
        } else {
            alert(result.message);
        }
    });

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

        const response = await fetch("/publish", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ caption, profile })
        });

        const result = await response.json();
        if (result.success) {
            alert(result.message);
            uploadedFiles = [];
            renderMediaList();
        } else {
            alert(result.message);
        }
    });

    function renderMediaList() {
        mediaList.innerHTML = "";
        uploadedFiles.forEach(file => {
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

    async function deleteMedia(filename) {
        const response = await fetch("/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename })
        });

        const result = await response.json();
        if (result.success) {
            uploadedFiles = result.files;
            renderMediaList();
        } else {
            alert(result.message);
        }
    }
});
