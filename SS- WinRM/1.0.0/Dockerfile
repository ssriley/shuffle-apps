# Base our app image off of the WALKOFF App SDK image
FROM frikky/shuffle:app_sdk as base

# We're going to stage away all of the bloat from the build tools so lets create a builder stage
FROM base as builder

# Install all alpine build tools needed for our pip installs
RUN apk --no-cache add --update alpine-sdk libffi libffi-dev musl-dev openssl-dev python3-dev krb5-libs krb5-dev krb5-conf keyutils-libs libcom_err libcrypto1.1 libssl1.1 libverto musl

# Install all of our pip packages in a single directory that we can copy to our base image later
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --prefix="/install" -r /requirements.txt

# Switch back to our base image and copy in all of our built packages and source code
FROM base
COPY --from=builder /install /usr/local
COPY src /app
RUN apk add curl

# Install any binary dependencies needed in our final image
# RUN apk --no-cache add --update my_binary_dependency
#RUN apk --no-cache add --update python3-dev krb5-libs krb5-dev krb5-conf keyutils-libs libcom_err libcrypto1.1 libssl1.1 libverto musl
# Finally, lets run our app!
WORKDIR /app
CMD python app.py --log-level DEBUG
