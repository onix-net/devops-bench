output "namespace" {
  value = var.namespace
}

output "ingress_class" {
  value = var.ingress_class
}

output "controller_service_name" {
  value = "ingress-nginx-controller"
}

output "controller_service_fqdn" {
  value = "ingress-nginx-controller.${var.namespace}.svc.cluster.local"
}
