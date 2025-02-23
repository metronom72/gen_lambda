import { APIGatewayEvent, APIGatewayProxyResult } from "aws-lambda";

export const lambda_handler = async (event: APIGatewayEvent): Promise<APIGatewayProxyResult> => {
  return {
    statusCode: 200,
    body: JSON.stringify({
      message: "Lambda Result",
      event: event
    }),
  };
};
