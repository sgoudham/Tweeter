package com.example;

import com.amazonaws.services.lambda.runtime.events.S3Event;
import com.amazonaws.services.lambda.runtime.events.SNSEvent;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micronaut.function.aws.MicronautRequestHandler;
import jakarta.inject.Inject;

public class TestRequestHandler extends MicronautRequestHandler<SNSEvent.SNS, Void> {

    @Inject
    ObjectMapper objectMapper;

    @Override
    public Void execute(SNSEvent.SNS input) {

        try {
            S3Event s3Event = objectMapper.readValue(input.getMessage(), S3Event.class);
            String message = s3Event.toString();
            System.out.println(message);
        } catch (JsonProcessingException jpe) {
            jpe.printStackTrace();
        }

        return null;
    }
}
