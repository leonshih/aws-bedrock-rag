"""
Base Infrastructure Stack

This stack includes all infrastructure components:
- VPC with public/private subnets
- Security Groups for ALB and Fargate
- ECS Cluster and Fargate Service
- Application Load Balancer
- ECR Repository
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr as ecr,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct


class BaseStack(Stack):
    """
    Base infrastructure stack for AWS Bedrock RAG API
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        env_config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.env_config = env_config

        # ============================================
        # VPC Configuration
        # ============================================
        vpc_config = self.env_config.get("vpc", {})
        
        self.vpc = ec2.Vpc(
            self, "RagVpc",
            max_azs=vpc_config.get("max_azs", 2),
            nat_gateways=vpc_config.get("nat_gateways", 1),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # ============================================
        # Security Groups
        # ============================================
        
        # ALB Security Group (allow HTTP/HTTPS from internet)
        self.alb_sg = ec2.SecurityGroup(
            self, "AlbSecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True
        )
        self.alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic from internet"
        )
        self.alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS traffic from internet"
        )

        # Fargate Security Group (allow traffic only from ALB)
        self.fargate_sg = ec2.SecurityGroup(
            self, "FargateSecurityGroup",
            vpc=self.vpc,
            description="Security group for Fargate tasks",
            allow_all_outbound=True
        )
        self.fargate_sg.add_ingress_rule(
            self.alb_sg,
            ec2.Port.tcp(8000),
            "Allow traffic from ALB"
        )

        # ============================================
        # ECR Repository
        # ============================================
        is_prod = self.env_name == "prod"
        
        self.ecr_repository = ecr.Repository(
            self, "RagApiRepository",
            repository_name=f"aws-bedrock-rag-api-{self.env_name}",
            removal_policy=RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY,
            empty_on_delete=not is_prod
        )

        # ============================================
        # ECS Cluster
        # ============================================
        self.cluster = ecs.Cluster(
            self, "RagCluster",
            vpc=self.vpc,
            cluster_name=f"bedrock-rag-cluster-{self.env_name}",
        )

        # ============================================
        # Fargate Service with ALB
        # ============================================
        ecs_config = self.env_config.get("ecs", {})
        
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "RagFargateService",
            cluster=self.cluster,
            cpu=ecs_config.get("cpu", 256),
            memory_limit_mib=ecs_config.get("memory", 512),
            desired_count=ecs_config.get("desired_count", 1),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(self.ecr_repository, tag="latest"),
                container_port=8000,
                container_name=f"rag-api-{self.env_name}"
            ),
            public_load_balancer=True,
            security_groups=[self.fargate_sg],
            assign_public_ip=False  # Tasks run in private subnet
        )

        # Configure health check
        self.fargate_service.target_group.configure_health_check(
            path="/health",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # ============================================
        # Outputs
        # ============================================
        CfnOutput(
            self, "Environment",
            value=self.env_name,
            description="Deployment environment",
            export_name=f"RagApi-{self.env_name}-Environment"
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=self.fargate_service.load_balancer.load_balancer_dns_name,
            description="DNS name of the Application Load Balancer",
            export_name=f"RagApi-{self.env_name}-LoadBalancerDNS"
        )

        CfnOutput(
            self, "EcrRepositoryUri",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI",
            export_name=f"RagApi-{self.env_name}-EcrUri"
        )

        CfnOutput(
            self, "ClusterName",
            value=self.cluster.cluster_name,
            description="ECS Cluster Name",
            export_name=f"RagApi-{self.env_name}-ClusterName"
        )
