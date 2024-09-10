### Install dependencies by running

`pip install -r requirements.txt`

### To run scripts

`python python_filename.py`

### To run the application
1. Download the [audio emotion classification model](https://dl.dropboxusercontent.com/scl/fi/433g0ochir0qnammjesix/model.safetensors?rlkey=14mzl4njkxksal2l87ojgzj4x&st=cv7z54ua&dl=1) to `user/models/grammermodels/audio_emotion`.  
    `wget -O /usr/src/app/users/models/audio_emotion/model.safetensors https://www.dropbox.com/scl/fi/433g0ochir0qnammjesix/model.safetensors?rlkey=14mzl4njkxksal2l87ojgzj4x&st=cv7z54ua&dl=1`
2. Download the [grammar model](https://dl.dropboxusercontent.com/scl/fi/mom43znri583up297cy2x/pytorch_model.bin?rlkey=hihv3xkeq74y86mft60xdemyk&st=qa0uljst&dl=1) to `user/models/grammermodels/grammermodels`.  
    `wget -O /usr/src/app/users/models/grammermodels/pytorch_model.bin https://www.dropbox.com/scl/fi/mom43znri583up297cy2x/pytorch_model.bin?rlkey=hihv3xkeq74y86mft60xdemyk&st=qa0uljst&dl=1`
3. Run following commands in order.  
`python manage.py makemigrations`  
`python manage.py migrate`  
`python manage.py runserver 8000`  


### To run in Docker container
1. Download the models using above scripts.
2. Run following command.  
    `sudo docker-compose up --build`