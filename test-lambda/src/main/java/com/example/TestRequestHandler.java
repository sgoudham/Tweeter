package com.example;

import com.amazonaws.services.lambda.runtime.events.SNSEvent;
import com.amazonaws.services.s3.event.S3EventNotification;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micronaut.function.aws.MicronautRequestHandler;
import jakarta.inject.Inject;

public class TestRequestHandler extends MicronautRequestHandler<SNSEvent, Void> {

    @Inject
    ObjectMapper objectMapper;

    @Override
    public Void execute(SNSEvent input) {
        System.out.println("##################################### Invocation Start #################################################");
        System.out.println("This is the SNSEvent: " + input.toString());

        try {
            S3EventNotification s3EventNotification = objectMapper.readValue(input.getRecords().get(0).getSNS().getMessage(), S3EventNotification.class);
            String message = s3EventNotification.toString();
            System.out.println("This is the s3EventNotification with ObjectMapper: " + message);
            System.out.println("This is the s3EventNotificationRecord: " + s3EventNotification.getRecords().get(0).toString());
            System.out.println("This is the s3EventNotificationRecord Arn: " + s3EventNotification.getRecords().get(0).getS3().getBucket().getArn());
            System.out.println("This is the s3EventNotificationRecord Key: " + s3EventNotification.getRecords().get(0).getS3().getObject().getKey());
        } catch (JsonProcessingException jpe) {
            jpe.printStackTrace();
        }

//        try {
//            Map<String, String> map = objectMapper.readValue(input.getRecords().get(0).getSNS().getMessage(), new TypeReference<HashMap<String,String>>() {});
//            String message = map.toString();
//            System.out.println("This is an S3Event Map" + message);
//        } catch (JsonProcessingException jpe) {
//            jpe.printStackTrace();
//        }
////
//
//        try {
//            S3EventNotification.S3EventNotificationRecord s3EventNotificationRecord = objectMapper.readValue(input.getRecords().get(0).getSNS().get., S3EventNotification.S3EventNotificationRecord.class);
//            String message = s3EventNotificationRecord.toString();
//            System.out.println("This is the s3EventRecordNotification: " + message);
//        } catch (JsonProcessingException jpe) {
//            jpe.printStackTrace();
//        }

        return null;
    }
}
