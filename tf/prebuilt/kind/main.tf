terraform {
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = ">= 0.5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.15.0"
    }
  }
}

provider "kind" {}

resource "kind_cluster" "default" {
  name            = var.cluster_name
  wait_for_ready  = true
  kubeconfig_path = pathexpand(var.kubeconfig_path)
}

provider "kubernetes" {
  host                   = kind_cluster.default.endpoint
  client_certificate     = kind_cluster.default.client_certificate
  client_key             = kind_cluster.default.client_key
  cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
}

provider "helm" {
  kubernetes {
    host                   = kind_cluster.default.endpoint
    client_certificate     = kind_cluster.default.client_certificate
    client_key             = kind_cluster.default.client_key
    cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
  }
}

module "ingress_nginx" {
  count  = var.install_ingress_nginx ? 1 : 0
  source = "../../modules/ingress-nginx"

  service_type  = var.ingress_service_type
  chart_version = var.ingress_chart_version
}

output "cluster_name" {
  value = kind_cluster.default.name
}

output "cluster_location" {
  value = "local"
}

output "ingress_class" {
  value = one(module.ingress_nginx[*].ingress_class)
}

output "ingress_controller_fqdn" {
  value = one(module.ingress_nginx[*].controller_service_fqdn)
}
