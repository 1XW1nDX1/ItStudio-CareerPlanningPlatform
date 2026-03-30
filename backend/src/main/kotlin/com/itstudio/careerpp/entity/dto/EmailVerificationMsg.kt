package com.itstudio.careerpp.entity.dto

import kotlinx.serialization.Serializable

@Serializable
data class EmailVerificationMsg(
    val email: String,
    val type: String,
    val code: String
)