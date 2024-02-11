import aws_cdk as core
import aws_cdk.assertions as assertions

from eks_python.eks_python_stack import EksPythonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in eks_python/eks_python_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EksPythonStack(app, "eks-python")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
