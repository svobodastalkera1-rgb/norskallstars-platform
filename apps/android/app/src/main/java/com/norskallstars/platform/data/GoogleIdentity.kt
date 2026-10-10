package com.norskallstars.platform.data

import android.app.Activity
import androidx.credentials.CredentialManager
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.NoCredentialException
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential

/** Provider proof is always challenge-bound and verified by the backend. */
class GoogleIdentity(private val activity: Activity, private val clientId: String) {
    suspend fun proof(api: Api): IdentityGoogleProof {
        check(clientId.isNotEmpty())
        val challenge = api.post<IdentityGoogleChallengeView, IdentityGoogleChallenge>(
            "/api/v1/identity/google/challenge", IdentityGoogleChallenge(clientId), false)
        val option = GetSignInWithGoogleOption.Builder(clientId).setNonce(challenge.nonce).build()
        val credential = try {
            CredentialManager.create(activity).getCredential(activity,
                GetCredentialRequest.Builder().addCredentialOption(option).build()).credential
        } catch (_: NoCredentialException) {
            throw ApiFailure(503)
        }
        check(credential.type == GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL)
        val token = GoogleIdTokenCredential.createFrom(credential.data).idToken
        return IdentityGoogleProof(challenge.challenge, token)
    }
}
