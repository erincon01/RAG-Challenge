

following the steps in this guide: https://towardsdatascience.com/beginner-guide-to-streamlit-deployment-on-azure-f6618eee1ba9

Part 2: Dockerize your Streamlit App
In part 2, we will take our Streamlit app and coordinate its deployment in Docker. Docker will containerize our app, making it ready for deployment on a variety of cloud platforms. If you don’t have Docker installed yet, click here.

To begin, we will create a Dockerfile in our project’s root directory (moving forward, all files created will be placed in the project’s root directory):

```bash
FROM mambaorg/micromamba:0.15.3
USER root
RUN mkdir /opt/RAG-CHALLENGE
RUN chmod -R 777 /opt/RAG-CHALLENGE
WORKDIR /opt/RAG-CHALLENGE
USER micromamba
COPY environment.yml environment.yml
RUN micromamba install -y -n base -f environment.yml && \
   micromamba clean --all --yes
COPY run.sh run.sh
COPY project_contents project_contents
USER root
RUN chmod a+x run.sh
CMD ["./run.sh"]
```

```bash
#!/bin/bash
streamlit run project_contents/app/app.py --theme.base "dark"
```

