variable "cluster_name" {
  type    = string
  default = "devops-bench-kind"
}

variable "location" {
  type    = string
  default = "local"
}

variable "kubeconfig_path" {
  type        = string
  description = "Path to write the kubeconfig file"
  default     = "~/.kube/config"
}

variable "install_ingress_nginx" {
  type        = bool
  description = "Whether to install the ingress-nginx controller via tf/modules/ingress-nginx."
  default     = false
}

variable "ingress_service_type" {
  type        = string
  description = "Controller Service type passed through to tf/modules/ingress-nginx."
  default     = "ClusterIP"
}

variable "ingress_chart_version" {
  type        = string
  description = "ingress-nginx helm chart version passed through to tf/modules/ingress-nginx."
  default     = "4.11.3"
}

