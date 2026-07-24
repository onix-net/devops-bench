terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.15.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = var.chart_version
  namespace        = var.namespace
  create_namespace = true
  wait             = var.wait_for_ready
  timeout          = 600

  set {
    name  = "controller.service.type"
    value = var.service_type
  }

  set {
    name  = "controller.ingressClassResource.name"
    value = var.ingress_class
  }

  set {
    name  = "controller.ingressClass"
    value = var.ingress_class
  }

  set {
    name  = "controller.admissionWebhooks.enabled"
    value = var.enable_admission_webhook
  }

  values = length(var.extra_values_yaml) > 0 ? [var.extra_values_yaml] : []
}
