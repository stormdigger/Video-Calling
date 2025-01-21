document.addEventListener('DOMContentLoaded', function () {
    const webcamElement = document.getElementById('webcam');
    const canvasElement = document.getElementById('canvas');
    const webcam = new Webcam(webcamElement, 'user', canvasElement);
    const form = document.getElementById('registrationForm');

    const img = document.getElementById('img-prev')
    let captureButton = document.getElementById('register-face-btn');
    let captureModal = new bootstrap.Modal(document.getElementById('captureModal'));
    let capButton = document.getElementById('capture-btn');

    let cameraStream;

    // Event listener for the "Register Face" button
    captureButton.addEventListener('click', () => {
        startCamera(); // Start the camera when the modal is opened
        captureModal.show(); // Show the modal
    });

    // Event listener to close the modal
    $('#captureModal').on('hidden.bs.modal', function (e) {
        console.log('Model closed',e)
        stopCamera(); // Stop the camera when the modal is closed
    });

    form.addEventListener('submit', ()=> {
        sessionStorage.setItem('username', form.username.value)
    })


    function dataUriToBlob(dataUri) {
        const splitDataUri = dataUri.split(',');
        const type = splitDataUri[0].split(':')[1].split(';')[0];
        const byteString = atob(splitDataUri[1]);
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const uint8Array = new Uint8Array(arrayBuffer);

        for (let i = 0; i < byteString.length; i++) {
            uint8Array[i] = byteString.charCodeAt(i);
        }

        return new Blob([arrayBuffer], { type: type });
    }
    
    function captureFrame() {
        let picture = webcam.snap();
        console.log('Picture captured');

        webcamElement.style.display = 'none';
        
        // Convert the base64 image data to a Blob object
        const blob = dataUriToBlob(picture);
        
        // Create a new File object from the Blob
        const file = new File([blob], 'capturedImage.png', { type: 'image/png' });

        // Create a new FileList containing the File object
        const fileList = new DataTransfer();
        fileList.items.add(file);

        // Create a new file input element
        const newInput = document.createElement('input');
        newInput.type = 'file';
        newInput.name = 'image';
        newInput.style.display = 'none';
        // Assign the FileList to the files property of the input element
        newInput.files = fileList.files;
        form.appendChild(newInput);

        img.src = URL.createObjectURL(blob);
        const errMsg = document.getElementById('error-message');
        

        let xhr = new XMLHttpRequest(),data=JSON.stringify({image:picture});
        xhr.onreadystatechange  = function () {
            if (xhr.status === 200) {
                // Handle the server's response, e.g., display a message to the user
                console.log(xhr.responseText);
                let response = JSON.parse(xhr.responseText);
                if(response.error) {
                    if(response.error === 'No Face Detected' || response.error ==='Image not Accepted'){
                        errMsg.innerText = response.error;
                        errMsg.style.display = 'block';
                        errMsg.classList.remove('d-none')
                        errMsg.classList.add('d-block')
                        img.style.boxShadow = '0px 0px 20px 0px red';
                    }
                    capButton.innerText = 'Recapture';
                    capButton.addEventListener('click', () => {
                        webcamElement.style.display = 'block';
                        errMsg.style.display = 'none';
                        img.src = '#';
                    })
                    console.log(response.error);
                }
                else {
                    let processedImageBase64 = response.processed_image;
                    img.src = 'data:image/png;base64,' + processedImageBase64;
                    img.style.boxShadow = '0px 0px 20px 0px green';
                    webcamElement.style.display = 'none';
                    errMsg.classList.add('d-none')
                    errMsg.classList.remove('d-block')
                    const submitModal = document.getElementById('submitModal-btn');
                    const registerButton = document.getElementById('registerButton')
    
                    document.getElementById('tick-icon').style.display = 'inline';
                    capButton.classList.add('disabled')
                    capButton.style.pointerEvents = 'none';
                    submitModal.classList.remove('disabled')
                    submitModal.style.pointerEvents = 'auto';
                    registerButton.classList.remove('disabled')
                    registerButton.style.pointerEvents = "auto";
                }
              
            } else {
                // Handle errors
                console.error('Error processing image:', xhr.statusText);
            }
        };
        xhr.open('POST', '/detectFace', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        // Set up a callback function to handle the server's response
        xhr.send(data);
    }

    $('#capture-btn').on('click',captureFrame);



    async function startCamera() {
        await webcam.start()
        .then(result =>{
            console.log("webcam started");
        })
        .catch(err => {
            console.log(err);
        });
    }

    async function stopCamera() {
        await webcam.stop();
    }

    function adjustModalSize() {
        const videoRatio = webcam.getAspectRatio();
        const modalBody = document.querySelector('.modal-body');
        const modalHeader = document.querySelector('.modal-header');
        const modalFooter = document.querySelector('.modal-footer');
        const modalContent = document.querySelector('.modal-content');
        const videoHeight =  videoRatio;
        modalBody.style.maxHeight = `${videoHeight}px`;
        const modalHeight =  modalBody.offsetHeight ;
        modalContent.style.height = `${modalHeight}px`;
    }
});