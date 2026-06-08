# Java Campaign

Use this reference for Java version migrations, Gradle/Maven modernization,
annotation processor failures, API moves, and large Java refactors.

## First Inspection Order

1. Build system: `settings.gradle*`, `build.gradle*`, `pom.xml`, wrappers, custom
   build logic, convention plugins, and CI images.
2. Java version controls: Gradle toolchains, Maven compiler plugin, `sourceCompatibility`,
   `targetCompatibility`, `--release`, `.java-version`, Docker images, IDE files.
3. Annotation/codegen: annotation processors, KAPT, Lombok, AutoValue, Immutables,
   protobuf, OpenAPI, JAXB, QueryDSL, generated sources.
4. Module and package boundaries: JPMS `module-info.java`, exported packages,
   public APIs, service loaders.
5. Runtime contracts: serialization, reflection, class loading, resources,
   JNI/JNA, logging, config, CLI.
6. Tests: unit framework, integration tests, test fixtures, test JVM args,
   bytecode agents, mocking libraries.

## Useful Tools

- Required/recommended: `git`, `rg`, repo build wrapper.
- Java: `javac`, `java`, `jdeps`, `jlink`, `jar`.
- Build: `gradle` or `mvn`.
- Optional: Error Prone, SpotBugs, Checkstyle, PMD, Revapi, japicmp.

Ask before installing missing tools. Prefer the repo wrapper over globally
installed Gradle or Maven.

## Risk Zones

- Annotation processors and bytecode tools often fail before source code does.
- Reflection and serialization can break while compilation still passes.
- Java version upgrades can be blocked by Gradle plugins, Maven plugins, CI
  images, test agents, or IDE metadata.
- `module-info.java` changes can alter service discovery and access rules.
- Public APIs include packages, annotations, generated types, serialized names,
  resources, and behavior used by plugins.

## Review Checklist

- Verify toolchain and runtime JDK match the target.
- Keep generated code regenerated, not hand-patched.
- Prefer small compatibility adapters during migrations.
- Cluster compile errors by dependency or API family before editing many files.
- Run narrow module tests first, then cross-module integration checks.
