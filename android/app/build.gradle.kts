import java.io.FileInputStream
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

// Secrets + machine-specific config live in gitignored local.properties, never in git.
val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) FileInputStream(f).use { load(it) }
}

android {
    namespace = "com.aiglass"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.aiglass"
        minSdk = 29          // Android 10 — DAT SDK requirement
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        // Meta DAT App ID, injected from local.properties (NOT the client token — Developer Mode
        // needs neither). Backend WS URL too: 10.0.2.2 = host machine from the Android emulator.
        manifestPlaceholders["mwdatAppId"] = localProps.getProperty("mwdat.application_id") ?: ""
        buildConfigField(
            "String",
            "BACKEND_WS_URL",
            "\"${localProps.getProperty("backend.ws_url") ?: "ws://10.0.2.2:8000/ws/ingest"}\"",
        )
    }

    buildFeatures { buildConfig = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation(libs.mwdat.core)
    implementation(libs.mwdat.camera)
    implementation(libs.mwdat.mockdevice)   // simulate Ray-Ban before your DAT access is approved
    implementation(libs.coroutines.android)
    implementation(libs.okhttp)
    implementation(libs.androidx.core)
    implementation(libs.androidx.appcompat)
    implementation(libs.lifecycle.runtime)
}
