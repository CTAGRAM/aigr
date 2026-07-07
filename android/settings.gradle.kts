import java.io.File
import java.io.FileInputStream
import java.util.Properties

pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)

    // GitHub Packages (where Meta ships the DAT SDK) needs a username + a classic PAT with
    // read:packages. Both are read from the gitignored local.properties (see local.properties.example).
    val localProps = Properties().apply {
        val f = File(rootDir, "local.properties")
        if (f.exists()) FileInputStream(f).use { load(it) }
    }

    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://maven.pkg.github.com/facebook/meta-wearables-dat-android")
            credentials {
                username = localProps.getProperty("github_user") ?: System.getenv("GITHUB_ACTOR") ?: ""
                password = localProps.getProperty("github_token") ?: System.getenv("GITHUB_TOKEN") ?: ""
            }
        }
    }
}

rootProject.name = "aiGlass"
include(":app")
