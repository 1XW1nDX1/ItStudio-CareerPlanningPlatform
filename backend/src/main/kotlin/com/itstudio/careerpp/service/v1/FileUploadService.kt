package com.itstudio.careerpp.service.v1

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile
import reactor.core.publisher.Mono
import java.io.File
import java.util.*

@Service
class FileUploadService(
    @Value($$"${app.file.direction}")
    private val fileDir: String
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    fun saveFile(file: MultipartFile): Mono<String> {
        val originalName = file.originalFilename ?: "unknown"
        val extension = originalName.substringAfterLast(".", "")
        val safeFileName = "${UUID.randomUUID()}.$extension"

        try {
            val targetFile = File("$fileDir/$safeFileName")
            file.transferTo(targetFile)
        } catch (e: Exception) {
            logger.error("Error while saving file", e)
            return Mono.just("Error while saving file")
        }
        
        return Mono.just("")
    }
}