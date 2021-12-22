# PDF Darkmode

##  🗒️ Convert Paper to Darkmode!
![main](./img/main.png)


## Install dependency
1. Install pdf2htmlEX
Visit https://github.com/pdf2htmlEX/pdf2htmlEX/releases

2. Create conda env
```
conda env create -f env.yaml
```

## Configuration
```config.json
{
    "input_dir" : "./input/", // input pdf dir 
    "output_dir" : "./output/" // output pdf dir
}
```

## Run script
```
conda activate pdf
python convert.py
```