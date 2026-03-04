# Helm Library

1. Chart Creation: Use the following command to create a library chart:
```
helm create my-library-chart --starter library-chart
```

2. Chart.yaml for a Library Chart: In the Chart.yaml file, you must specify that this chart is a library:

```
apiVersion: v2
name: my-library-chart
type: library
version: 0.1.0
```

3. Adding Helper Templates: Place your helper templates inside the templates/_helpers.tpl file or other template files. For example:
```
{{- define "my-library.fullname" -}}
{{ printf "%s-%s" .Release.Name .Chart.Name }}
{{- end -}}
```

### Using a Library Chart in Another Chart

1. Add the Library Chart as a Dependency: In the consumer chart's Chart.yaml, add the library chart as a dependency:

```
dependencies:
  - name: my-library-chart
    version: 0.1.0
    repository: "file://../my-library-chart"
```

2. Update Dependencies: Run the following command to update the dependencies:

```
helm dependency update
```
3. Referencing Library Templates: In the consumer chart, you can call functions from the library chart like this:

```
metadata:
  name: {{ include "my-library.fullname" . }}
```