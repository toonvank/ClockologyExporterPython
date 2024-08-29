let errorMessage = document.getElementById('errorMessage');
let error = document.getElementById('error');

document.getElementById('file').addEventListener('change', function() {
    document.querySelector('.mt-8').style.display = 'none';
    document.getElementById('viewButton').innerText = `View Clock Face Contents 📦`;
    error.style.display = 'none';
} );

document.getElementById('viewButton').addEventListener('click', function() {
    error.style.display = 'none';
    document.querySelector('.mt-8').style.display = 'none';
    document.getElementById('viewButton').innerText = `View Clock Face Contents 📦`;

    const fileInput = document.getElementById('file');
    const formData = new FormData();

    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    } else {
        error.style.display = 'block';
        errorMessage.innerText = 'Please select a file to upload';
        return;
    }

    // Check if file is in clock2 format
    const file = fileInput.files[0];
    if (file.name.split('.').pop() !== 'clock2') {
        error.style.display = 'block';
        errorMessage.innerText = 'Please select a clock2 file';
        return;
    }

    document.querySelector('.mt-8').style.display = 'none';
    document.getElementById('loading').style.display = 'block';

    fetch('/api/clockface', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())  // Parse the JSON response
    .then(data => {
        document.getElementById('loading').style.display = 'none';

        if (data.error) {
            error.style.display = 'block';
            errorMessage.innerText = data.error;
            return;
        }

        document.querySelector('.mt-8').style.display = 'block';

        // Clear any previous content
        const contentContainer = document.getElementById('imageContainer');
        contentContainer.innerHTML = '';

        // Add new files (images and non-images) to the page
        data.files.forEach((file, idx) => {
            const fileElement = document.createElement('div');
            fileElement.style.margin = '10px';
            fileElement.style.maxWidth = '200px';
            fileElement.style.textAlign = 'center';

            let extension;
            switch (file.file_type) {
                case 'application/font-sfnt':
                    extension = 'ttf';
                    break;
                case 'video/quicktime':
                    extension = 'mov';
                    break;
                default:
                    extension = file.file_type.split('/').pop();
                    break;
            }

            if (file.file_type.startsWith('image/')) {
                // Display the image
                const imgElement = document.createElement('img');
                imgElement.src = `data:${file.file_type};base64,${file.content}`;
                imgElement.alt = `Image ${idx + 1}`;
                imgElement.style.maxWidth = '200px';
                imgElement.style.maxHeight = '200px';

                imgElement.addEventListener('click', function() {
                    const a = document.createElement('a');
                    a.href = imgElement.src;
                    a.download = `image-${idx + 1}.png`;
                    a.click();
                });

                imgElement.addEventListener('mouseover', function() {
                    imgElement.style.cursor = 'pointer';
                });

                imgElement.addEventListener('mouseenter', function() {
                    imgElement.style.border = '2px solid black';
                    imgElement.style.maxWidth = '300px';
                });

                imgElement.addEventListener('mouseleave', function() {
                    imgElement.style.border = 'none';
                    imgElement.style.maxWidth = '200px';
                });

                fileElement.appendChild(imgElement);
            } else {
                // Display the file type and a download link
                const fileTypeElement = document.createElement('p');
                fileTypeElement.innerText = `File Type: ${file.file_type}`;

                const downloadLink = document.createElement('a');
                downloadLink.href = `data:${file.file_type};base64,${file.content}`;
                downloadLink.download = `file-${idx + 1}.${extension}`;
                downloadLink.innerText = `Download ${extension.toUpperCase()} File`;
                downloadLink.style.display = 'block';
                downloadLink.style.marginTop = '10px';

                fileElement.appendChild(fileTypeElement);
                fileElement.appendChild(downloadLink);

                fileElement.addEventListener('click', function() {
                    downloadLink.click();
                });

                fileElement.addEventListener('mouseover', function() {
                    fileElement.style.cursor = 'pointer';
                });

                fileElement.addEventListener('mouseenter', function() {
                    fileElement.style.border = '2px solid black';
                    fileElement.style.maxWidth = '300px';
                });

                fileElement.addEventListener('mouseleave', function() {
                    fileElement.style.border = 'none';
                    fileElement.style.maxWidth = '200px';
                });

                // Show a file icon for non-image files
                const iconElement = document.createElement('img');
                iconElement.src = '/static/images/file.png';  // Assuming a generic file icon is available
                iconElement.alt = `File ${idx + 1}`;
                iconElement.style.maxWidth = '100px';
                iconElement.style.maxHeight = '100px';
                iconElement.style.margin = 'auto';
                fileElement.appendChild(iconElement);
            }

            contentContainer.appendChild(fileElement);
        });

        document.getElementById('viewButton').innerText = `Extracted ${data.files.length} files successfully ✅`;
    })
    .catch(error => {
        document.getElementById('loading').style.display = 'none';
        console.error('Error:', error);
    });
});

document.getElementById('downloadZip').addEventListener('click', function() {
    const zip = new JSZip();
    const contentContainer = document.getElementById('imageContainer');
    const items = contentContainer.children;

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const imgElement = item.querySelector('img');
        const linkElement = item.querySelector('a');
        const fileTypeElement = item.querySelector('p');

        let extension;
        if (fileTypeElement) {
            const fileType = fileTypeElement.innerText.split(': ')[1];
            switch (fileType) {
                case 'application/font-sfnt':
                    extension = 'ttf';
                    break;
                case 'video/quicktime':
                    extension = 'mov';
                    break;
                default:
                    extension = fileType.split('/').pop();
                    break;
            }
        }

        if (imgElement && imgElement.src.startsWith('data:image/')) {
            const imgData = imgElement.src.split(',')[1];
            zip.file(`image-${i + 1}.png`, imgData, { base64: true });
        } else if (linkElement) {
            const fileData = linkElement.href.split(',')[1];
            zip.file(`file-${i + 1}.${extension}`, fileData, { base64: true });
        }
    }

    zip.generateAsync({ type: 'blob' }).then(content => {
        saveAs(content, 'files.zip');
    });
});