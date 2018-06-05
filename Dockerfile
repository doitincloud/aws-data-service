##
# Copyright 2017 Sam Wen.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##
FROM python:3.6-alpine

RUN apk update 
RUN apk upgrade

# common tool sets
#
RUN apk add --no-cache bash wget curl jq git mysql-client openssh-client git zip tree

# dependencies of awscli
#
RUN apk -Uuv add groff less

# install awscli
# 
RUN pip install awscli

# install validate_email
#
RUN pip install validate_email

RUN rm -rf /var/cache/apk/*

WORKDIR /workspace

RUN mkdir -p /lib-default

COPY deployment/lib/*.jar /lib-default
