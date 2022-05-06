########################################################
# docker build -t essen1999/nafld_kbd:0.0.1 .
# docker run -it --rm -p 8501:8501 essen1999/nafld_kbd:0.0.1
########################################################
FROM python:3.9-slim
EXPOSE 8501
WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -rf /root/.cache/pip
CMD ["streamlit", "run", "nafld_kbd.py"]
