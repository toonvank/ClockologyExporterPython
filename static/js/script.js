let errorMessage = document.getElementById('errorMessage')
let error = document.getElementById('error')
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

        //check if file is in watch2 format
        const file = fileInput.files[0];
        if (file.name.split('.').pop() !== 'clock2') {
            error.style.display = 'block';
            errorMessage.innerText = 'Please select a clock2 file';
            return
        }

        document.querySelector('.mt-8').style.display = 'none';
        document.getElementById('loading').style.display = 'block';
        fetch('/api/clockface', {
        method: 'POST',
        body: formData
        })
        .then(response => response.json())  // Parse the JSON response
        .then(data => {
            if (data.error) {
                document.getElementById('loading').style.display = 'none';
                error.style.display = 'block';
                errorMessage.innerText = data.error;
                return;
            }
            document.querySelector('.mt-8').style.display = 'block';

            // Clear any previous images
            const imageContainer = document.getElementById('imageContainer');
            imageContainer.innerHTML = '';

            // Add new images to the page
            data.images.forEach((imgStr, idx) => {
                const imgElement = document.createElement('img');
                imgElement.src = `data:image/png;base64,${imgStr}`;
                imgElement.alt = `Image ${idx + 1}`;
                imgElement.style.margin = '10px';
                imgElement.style.maxWidth = '200px'; // Adjust the size as needed
                imgElement.style.maxHeight = '200px'; // Adjust the size as needed
                imageContainer.appendChild(imgElement);
                //download on click image
                imgElement.addEventListener('click', function() {
                    const a = document.createElement('a');
                    a.href = `data:image/png;base64,${imgStr}`;
                    a.download = `image-${idx + 1}.png`;
                    a.click();
                });
                imgElement.addEventListener('mouseover', function() {
                    imgElement.style.cursor = 'pointer';
                });
                imgElement.addEventListener('mouseenter', function() {
                    imgElement.style.border = '2px solid black';
                    //make image bigger
                    imgElement.style.maxWidth = '300px'; // Adjust the size as needed
                });
                imgElement.addEventListener('mouseleave', function() {
                    imgElement.style.border = 'none';
                    imgElement.style.maxWidth = '200px'; // Adjust the size as needed
                });
            });
            document.getElementById('loading').style.display = 'none';
            document.getElementById('viewButton').innerText = `Extracted ${data.images.length} images successfully ✅`;
        })
        .catch(error => {
            //remove loading spinner
            document.getElementById('loading').style.display = 'none';
            console.error('Error:', error);
        });
    });
document.getElementById('downloadZip').addEventListener('click', function() {
    const images = document.getElementById('imageContainer').querySelectorAll('img');
    const zip = new JSZip();
    images.forEach((img, idx) => {
        const imgData = img.src.split(',')[1];
        zip.file(`image-${idx + 1}.png`, imgData, {base64: true});
    });
    zip.generateAsync({type: 'blob'}).then(content => {
        saveAs(content, 'images.zip');
    });
});