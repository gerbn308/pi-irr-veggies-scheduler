docker build -f Dockerfile -t python-irrigation:latest .;
docker tag python-irrigation:latest localhost:5000/python-irrigation;
docker push localhost:5000/python-irrigation;
