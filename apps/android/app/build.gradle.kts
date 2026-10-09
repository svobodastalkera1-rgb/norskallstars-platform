plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val apiOrigin = providers.gradleProperty("apiOrigin").orElse("https://api.invalid").get()
val googleClient = providers.gradleProperty("googleClientId").orElse("").get()
val developmentOrigin = providers.gradleProperty("developmentOrigin").orElse("http://10.0.2.2:8000").get()
require(developmentOrigin.matches(Regex("http://(10\\.0\\.2\\.2|127\\.0\\.0\\.1|localhost):[0-9]{1,5}")) ||
    developmentOrigin.matches(Regex("https://[A-Za-z0-9.-]+(:[0-9]+)?")))
require(apiOrigin.matches(Regex("https://[A-Za-z0-9.-]+(:[0-9]+)?"))) {
    "apiOrigin must be an HTTPS origin without credentials, path or query"
}
require(googleClient.matches(Regex("[A-Za-z0-9._-]*")))

android {
    namespace = "com.norskallstars.platform"
    compileSdk = 36
    buildToolsVersion = "36.0.0"
    defaultConfig {
        applicationId = "com.norskallstars.platform"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.6.0-dev"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "API_ORIGIN", "\"$apiOrigin\"")
        buildConfigField("String", "GOOGLE_CLIENT_ID", "\"$googleClient\"")
    }
    buildTypes {
        debug {
            applicationIdSuffix = ".dev"
            buildConfigField("String", "API_ORIGIN", "\"$developmentOrigin\"")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    lint {
        abortOnError = true
        warningsAsErrors = true
        // Versions are deliberately pinned/locked and audited by OSV + Dependabot.
        // Network-driven update suggestions are not correctness/security checks.
        disable += setOf("GradleDependency", "NewerVersionAvailable", "AndroidGradlePluginVersion", "OldTargetApi")
    }
    bundle { language { enableSplit = false } }
    testOptions {
        animationsDisabled = true
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        allWarningsAsErrors.set(true)
    }
}

dependencyLocking { lockAllConfigurations() }

// Remediate known transitive tool/test findings; never exclude them from the audit.
configurations.configureEach {
    resolutionStrategy.eachDependency {
        when {
            requested.group == "org.bouncycastle" -> useVersion("1.86")
            requested.group == "org.apache.commons" && requested.name == "commons-lang3" -> useVersion("3.20.0")
            requested.group == "org.apache.httpcomponents" && requested.name == "httpclient" -> useVersion("4.5.14")
                requested.group == "org.bitbucket.b_c" && requested.name == "jose4j" -> useVersion("0.9.6")
                requested.group == "org.jdom" && requested.name == "jdom2" -> useVersion("2.0.6.1")
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2025.10.01")
    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.4")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.4")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:5.3.0")
    implementation("androidx.credentials:credentials:1.5.0")
    implementation("androidx.credentials:credentials-play-services-auth:1.5.0")
    implementation("com.google.android.libraries.identity.googleid:googleid:1.1.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
    testImplementation("com.squareup.okhttp3:mockwebserver3:5.3.0")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
