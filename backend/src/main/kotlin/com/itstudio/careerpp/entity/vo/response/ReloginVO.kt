package com.itstudio.careerpp.entity.vo.response

import kotlinx.serialization.Serializable

@Serializable
data class ReloginVO(
    val token: String = "",
    val expire: String = "",
)