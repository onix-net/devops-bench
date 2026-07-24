variable "chart_version" {
  type        = string
  description = "Pinned ingress-nginx helm chart version (this pins controller v1.11.x)."
  default     = "4.11.3"
}

variable "namespace" {
  type        = string
  description = "Namespace the controller is installed into."
  default     = "ingress-nginx"
}

variable "ingress_class" {
  type        = string
  description = "IngressClass name the controller watches and Ingress resources reference."
  default     = "nginx"
}

variable "service_type" {
  type        = string
  description = "Controller Service type. ClusterIP avoids kind's LoadBalancer-pending state and lets in-cluster http_probe checks reach the controller by FQDN."
  default     = "ClusterIP"
}

variable "enable_admission_webhook" {
  type        = bool
  description = "Whether the ValidatingAdmissionWebhook is enabled. Disabled by default: it is flaky on kind and blocks repeated Ingress fixture applies during isorun iteration."
  default     = false
}

variable "wait_for_ready" {
  type        = bool
  description = "Whether tofu waits for the helm release's resources to become ready before returning."
  default     = true
}

variable "extra_values_yaml" {
  type        = string
  description = "Raw helm values YAML passthrough for overrides not covered by the pinned variables above."
  default     = ""
}
