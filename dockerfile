FROM python:3.8-alpine
ADD . /opt/bat
WORKDIR /opt/bat

# install the module
RUN pip install .
# Run unittests, fails the build on failing tests
RUN python -m unittest discover bat.tests -p '*_test.py'

# when called with docker run, execute the bat command with arguments
# EX: docker run bat --help
ENTRYPOINT ["bat"]
# Use bat cli to start the service
CMD ["start"]
