document.addEventListener('DOMContentLoaded', function() {

    let lobby_form = document.getElementById('lobby__form')

    let displayName = lobby_form.name.value;
    let username = sessionStorage.getItem('username')
    username = username[0].toUpperCase() + username.substring(1);
    let user = document.getElementById('user')
    if(username != null){
        user.innerText = 'Hello ' + username;
    }

    console.log(username);
    
    const webcamElement = document.getElementById('webcam');
    const canvasElement = document.getElementById('canvas');
    const webcam = new Webcam(webcamElement, 'user', canvasElement);
    let submit_btn = document.getElementById('submit-btn');
    let modal = new bootstrap.Modal(document.getElementById('captureModal'));

    submit_btn.addEventListener('click', ()=> {
            startCamera(); 
            modal.show();
            const intervalTime = 1000;

            const repetitions = 5;
            let currentRepetition = 0;

            const intervalId = setInterval(function () {
                captureFrame();
                currentRepetition++;
                if (currentRepetition >= repetitions) {
                    clearInterval(intervalId);
                    webcamElement.style.boxShadow = '0px 0px 20px 1px red';
                }
            }, intervalTime);
    })

    $('#captureModal').on('hidden.bs.modal', function (e) {
        console.log('Model closed',e)
        stopCamera(); 
    });

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
        const blob = dataUriToBlob(picture);
        const file = new File([blob], 'capturedImage.png', { type: 'image/png' });
        const fileList = new DataTransfer();
        fileList.items.add(file);
        const errMsg = document.getElementById('error-message');
        

        let xhr = new XMLHttpRequest(),data=JSON.stringify({name:username, image:picture, source: 'lobby'});
        xhr.onreadystatechange  = function () {
            if (xhr.status === 200) {
                console.log(xhr.responseText);
                let response = JSON.parse(xhr.responseText);
                if(response.error) {
                    if(response.error === 'No Face Detected'){
                        errMsg.innerText = response.error;
                        errMsg.style.display = 'block';
                        errMsg.classList.remove('d-none')
                        errMsg.classList.add('d-block')
                    }
                    console.log(response.error);
                }
                else {
                    console.log(response.faceMatch)
                    if(response.faceMatch === true){
                        webcamElement.style.boxShadow = '0px 0px 20px 1px green';
                        console.log(response.room_id)
                        const redirectURL = (response.redirect === 'room') ? `room/${lobby_form.room.value}` : 'lobby';
        
                        sessionStorage.setItem('display_name', lobby_form.name.value);
                        if(lobby_form.room.value === '') lobby_form.room.value = Math.floor(Math.random()*10000)
                        window.location = redirectURL;
                    } else {
                        webcamElement.style.boxShadow = '0px 0px 20px 1px red';
                    }
                    errMsg.classList.add('d-none')
                    errMsg.classList.remove('d-block')
                }
            
            } else {
                console.error('Error processing image:', xhr.statusText);
            }
        };

        xhr.open('POST', '/verifyFace', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(data);
    }


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
        const modalContent = document.querySelector('.modal-content');
        const videoHeight =  videoRatio;
        modalBody.style.maxHeight = `${videoHeight}px`;
        const modalHeight =  modalBody.offsetHeight ;
        modalContent.style.height = `${modalHeight}px`;
    }


    lobby_form.addEventListener('submit', (e) => {
        console.log('Form submitted');
        e.preventDefault()
        sessionStorage.setItem('display_name',lobby_form.name.value)
        let inviteCode = lobby_form.room.value
        if(!inviteCode) {
            inviteCode = String(Math.floor(Math.random()*10000))
        }
        // Use consistent navigation logic based on the response
        if (response.faceMatch === true) {
            window.location = (response.redirect === 'room') ? `room/${inviteCode}` : 'lobby';
        }
    })


})
