buildscript {
    configurations.classpath {
        resolutionStrategy.activateDependencyLocking()
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
        // Override AGP's bundled KGP: fixes GHSA-r937-wjx7-w2jp.
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.4.20")
    }
}

plugins {
    id("com.android.application") version "9.4.1" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.20" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "2.4.20" apply false
}
