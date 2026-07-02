FROM xemuliam/dbt:2.0.0-preview.178-fusion

COPY . /modeling/

WORKDIR /modeling/

CMD ["dbt", "build"]