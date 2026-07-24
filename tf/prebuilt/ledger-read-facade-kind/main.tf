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
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0.0"
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
  source = "../../modules/ingress-nginx"

  service_type  = "ClusterIP"
  chart_version = "4.11.3"
}

# Seeds the broken ledger-read-facade fixture during `tofu apply`, once
# ingress-nginx is up, so the task provisions already-broken.
resource "null_resource" "seed" {
  depends_on = [module.ingress_nginx]

  triggers = {
    cluster = kind_cluster.default.name
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = "${path.module}/scripts/setup.sh"
    environment = {
      KUBECONFIG    = pathexpand(var.kubeconfig_path)
      MANIFESTS_DIR = "${path.module}/manifests"
      NAMESPACE     = "ledger"
    }
  }
}

output "cluster_name" {
  value = kind_cluster.default.name
}

output "cluster_location" {
  value = "local"
}

output "ingress_class" {
  value = module.ingress_nginx.ingress_class
}

output "ingress_controller_fqdn" {
  value = module.ingress_nginx.controller_service_fqdn
}
