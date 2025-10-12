#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel de Performance para Gradio UI
"""

import gradio as gr
import json
from typing import Dict, Any, Optional
from src.agents.orchestration import WorkflowEngine
from src.utils.logger import setup_logger

logger = setup_logger()


class PerformancePanel:
    """Panel de visualización de métricas de performance"""
    
    def __init__(self, workflow_engine: Optional[WorkflowEngine] = None):
        """
        Inicializa el panel de performance
        
        Args:
            workflow_engine: Instancia del workflow engine (opcional)
        """
        self.workflow_engine = workflow_engine or WorkflowEngine()
        logger.info("PerformancePanel initialized")
    
    def get_global_metrics(self) -> str:
        """Obtiene métricas globales del sistema"""
        try:
            metrics = self.workflow_engine.get_metrics()
            
            # Formatear métricas para visualización
            output = "# 📊 Métricas Globales del Sistema\n\n"
            
            # Métricas de workflow
            output += "## Workflows\n"
            output += f"- **Total ejecutados**: {metrics.get('total_workflows', 0)}\n"
            output += f"- **Exitosos**: {metrics.get('successful_workflows', 0)}\n"
            output += f"- **Fallidos**: {metrics.get('failed_workflows', 0)}\n"
            output += f"- **Tiempo promedio**: {metrics.get('avg_execution_time_ms', 0):.2f}ms\n\n"
            
            # Métricas de performance
            perf_metrics = metrics.get('performance_metrics', {})
            if perf_metrics:
                output += "## Performance\n"
                output += f"- **Total requests**: {perf_metrics.get('total_requests', 0)}\n"
                output += f"- **Tasa de éxito**: {perf_metrics.get('success_rate', 0)*100:.1f}%\n"
                output += f"- **Latencia promedio**: {perf_metrics.get('avg_duration_ms', 0):.2f}ms\n"
                output += f"- **Throughput**: {perf_metrics.get('throughput_per_second', 0):.2f} req/s\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting global metrics: {e}")
            return f"❌ Error al obtener métricas: {str(e)}"
    
    def get_agent_metrics(self) -> str:
        """Obtiene métricas de todos los agentes"""
        try:
            report = self.workflow_engine.get_performance_report()
            perf_report = report.get('performance_report', {})
            agent_metrics = perf_report.get('agent_metrics', {})
            
            if not agent_metrics:
                return "ℹ️ No hay métricas de agentes disponibles aún.\n\nEjecuta algunas consultas para generar métricas."
            
            output = "# 🤖 Métricas por Agente\n\n"
            
            for agent_name, metrics in agent_metrics.items():
                if metrics.get('no_data'):
                    continue
                
                output += f"## {agent_name}\n"
                output += f"- **Requests**: {metrics.get('total_requests', 0)}\n"
                output += f"- **Tasa de éxito**: {metrics.get('success_rate', 0)*100:.1f}%\n"
                output += f"- **Latencia promedio**: {metrics.get('avg_duration_ms', 0):.2f}ms\n"
                
                # Percentiles si están disponibles
                if 'p95_duration_ms' in metrics:
                    output += f"- **P95**: {metrics['p95_duration_ms']:.2f}ms\n"
                if 'p99_duration_ms' in metrics:
                    output += f"- **P99**: {metrics['p99_duration_ms']:.2f}ms\n"
                
                output += "\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting agent metrics: {e}")
            return f"❌ Error al obtener métricas de agentes: {str(e)}"
    
    def get_circuit_breaker_status(self) -> str:
        """Obtiene estado de los circuit breakers"""
        try:
            metrics = self.workflow_engine.circuit_breaker_manager.get_all_metrics()
            healthy = self.workflow_engine.circuit_breaker_manager.get_healthy_agents()
            
            if not metrics:
                return "ℹ️ No hay circuit breakers activos."
            
            output = "# 🔌 Estado de Circuit Breakers\n\n"
            output += f"**Agentes saludables**: {len(healthy)}/{len(metrics)}\n\n"
            
            for agent_name, agent_metrics in metrics.items():
                state = agent_metrics.get('state', 'unknown')
                
                # Emoji según estado
                if state == 'closed':
                    emoji = "✅"
                    color = "verde"
                elif state == 'open':
                    emoji = "🔴"
                    color = "rojo"
                else:  # half_open
                    emoji = "🟡"
                    color = "amarillo"
                
                output += f"## {emoji} {agent_name} ({state.upper()})\n"
                output += f"- **Llamadas totales**: {agent_metrics.get('total_calls', 0)}\n"
                output += f"- **Exitosas**: {agent_metrics.get('successful_calls', 0)}\n"
                output += f"- **Fallidas**: {agent_metrics.get('failed_calls', 0)}\n"
                output += f"- **Rechazadas**: {agent_metrics.get('rejected_calls', 0)}\n"
                output += f"- **Fallos consecutivos**: {agent_metrics.get('failure_count', 0)}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting circuit breaker status: {e}")
            return f"❌ Error al obtener estado de circuit breakers: {str(e)}"
    
    def get_slow_agents(self, threshold_ms: float = 5000.0) -> str:
        """Obtiene agentes lentos"""
        try:
            slow_agents = self.workflow_engine.performance_monitor.get_slow_agents(threshold_ms)
            
            if not slow_agents:
                return f"✅ No hay agentes lentos (umbral: {threshold_ms}ms)"
            
            output = f"# 🐌 Agentes Lentos (>{threshold_ms}ms)\n\n"
            output += f"**Total detectados**: {len(slow_agents)}\n\n"
            
            for agent in slow_agents:
                output += f"## ⚠️ {agent['agent_name']}\n"
                output += f"- **Latencia promedio**: {agent['avg_duration_ms']:.2f}ms\n"
                output += f"- **Requests**: {agent['total_requests']}\n"
                output += f"- **Tasa de éxito**: {agent['success_rate']*100:.1f}%\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting slow agents: {e}")
            return f"❌ Error al obtener agentes lentos: {str(e)}"
    
    def get_failing_agents(self, threshold_rate: float = 0.1) -> str:
        """Obtiene agentes con fallos"""
        try:
            failing_agents = self.workflow_engine.performance_monitor.get_failing_agents(threshold_rate)
            
            if not failing_agents:
                return f"✅ No hay agentes con fallos (umbral: {threshold_rate*100:.0f}%)"
            
            output = f"# ❌ Agentes con Fallos (>{threshold_rate*100:.0f}%)\n\n"
            output += f"**Total detectados**: {len(failing_agents)}\n\n"
            
            for agent in failing_agents:
                output += f"## 🔴 {agent['agent_name']}\n"
                output += f"- **Tasa de fallos**: {agent['failure_rate']*100:.1f}%\n"
                output += f"- **Requests fallidos**: {agent['failed_requests']}/{agent['total_requests']}\n"
                output += f"- **Latencia promedio**: {agent['avg_duration_ms']:.2f}ms\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting failing agents: {e}")
            return f"❌ Error al obtener agentes con fallos: {str(e)}"
    
    def get_load_balancer_stats(self) -> str:
        """Obtiene estadísticas del load balancer"""
        try:
            metrics = self.workflow_engine.load_balancer.get_metrics()
            all_stats = self.workflow_engine.load_balancer.get_all_stats()
            
            output = "# ⚖️ Load Balancer\n\n"
            output += f"**Estrategia**: {metrics.get('strategy', 'unknown')}\n"
            output += f"**Total requests**: {metrics.get('total_requests', 0)}\n"
            output += f"**Requests balanceados**: {metrics.get('balanced_requests', 0)}\n"
            output += f"**Agentes activos**: {metrics.get('total_agents', 0)}\n"
            output += f"**Conexiones activas**: {metrics.get('total_active_connections', 0)}\n\n"
            
            if all_stats:
                output += "## Estadísticas por Agente\n\n"
                for agent_name, stats in all_stats.items():
                    if stats:
                        output += f"### {agent_name}\n"
                        output += f"- **Conexiones activas**: {stats.get('active_connections', 0)}\n"
                        output += f"- **Load score**: {stats.get('load_score', 0):.2f}\n"
                        output += f"- **Tiempo respuesta promedio**: {stats.get('avg_response_time', 0):.2f}s\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting load balancer stats: {e}")
            return f"❌ Error al obtener estadísticas del load balancer: {str(e)}"
    
    def reset_circuit_breaker(self, agent_name: str) -> str:
        """Resetea un circuit breaker"""
        try:
            if not agent_name or agent_name.strip() == "":
                return "⚠️ Por favor ingresa el nombre de un agente"
            
            breaker = self.workflow_engine.circuit_breaker_manager.get_breaker(agent_name)
            breaker.reset()
            
            return f"✅ Circuit breaker de '{agent_name}' reseteado exitosamente"
            
        except Exception as e:
            logger.error(f"Error resetting circuit breaker: {e}")
            return f"❌ Error al resetear circuit breaker: {str(e)}"
    
    def get_full_report(self) -> str:
        """Genera un reporte completo"""
        try:
            report = self.workflow_engine.get_performance_report()
            
            # Convertir a JSON formateado
            return json.dumps(report, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error generating full report: {e}")
            return f"❌ Error al generar reporte: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Crea la interfaz Gradio para el panel de performance"""
        with gr.Blocks() as interface:
            gr.Markdown("# 📊 Panel de Performance")
            gr.Markdown("Monitoreo en tiempo real del sistema de orquestación de agentes")
            
            with gr.Tabs():
                # Tab 1: Métricas Globales
                with gr.Tab("📈 Métricas Globales"):
                    global_btn = gr.Button("🔄 Actualizar Métricas", variant="primary")
                    global_output = gr.Markdown()
                    global_btn.click(
                        fn=self.get_global_metrics,
                        outputs=global_output
                    )
                
                # Tab 2: Métricas por Agente
                with gr.Tab("🤖 Agentes"):
                    agent_btn = gr.Button("🔄 Actualizar Agentes", variant="primary")
                    agent_output = gr.Markdown()
                    agent_btn.click(
                        fn=self.get_agent_metrics,
                        outputs=agent_output
                    )
                
                # Tab 3: Circuit Breakers
                with gr.Tab("🔌 Circuit Breakers"):
                    cb_btn = gr.Button("🔄 Actualizar Estado", variant="primary")
                    cb_output = gr.Markdown()
                    
                    gr.Markdown("### Reset Manual")
                    with gr.Row():
                        agent_name_input = gr.Textbox(
                            label="Nombre del Agente",
                            placeholder="Ej: QueryAgent"
                        )
                        reset_btn = gr.Button("⚡ Reset Circuit Breaker", variant="secondary")
                    reset_output = gr.Textbox(label="Resultado")
                    
                    cb_btn.click(
                        fn=self.get_circuit_breaker_status,
                        outputs=cb_output
                    )
                    reset_btn.click(
                        fn=self.reset_circuit_breaker,
                        inputs=agent_name_input,
                        outputs=reset_output
                    )
                
                # Tab 4: Alertas
                with gr.Tab("⚠️ Alertas"):
                    with gr.Row():
                        slow_threshold = gr.Number(
                            label="Umbral de latencia (ms)",
                            value=5000
                        )
                        fail_threshold = gr.Number(
                            label="Umbral de fallos (%)",
                            value=10
                        )
                    
                    alert_btn = gr.Button("🔄 Verificar Alertas", variant="primary")
                    
                    gr.Markdown("### Agentes Lentos")
                    slow_output = gr.Markdown()
                    
                    gr.Markdown("### Agentes con Fallos")
                    fail_output = gr.Markdown()
                    
                    alert_btn.click(
                        fn=lambda t: self.get_slow_agents(t),
                        inputs=slow_threshold,
                        outputs=slow_output
                    )
                    alert_btn.click(
                        fn=lambda t: self.get_failing_agents(t/100),
                        inputs=fail_threshold,
                        outputs=fail_output
                    )
                
                # Tab 5: Load Balancer
                with gr.Tab("⚖️ Load Balancer"):
                    lb_btn = gr.Button("🔄 Actualizar Estadísticas", variant="primary")
                    lb_output = gr.Markdown()
                    lb_btn.click(
                        fn=self.get_load_balancer_stats,
                        outputs=lb_output
                    )
                
                # Tab 6: Reporte Completo
                with gr.Tab("📋 Reporte JSON"):
                    report_btn = gr.Button("📥 Generar Reporte Completo", variant="primary")
                    report_output = gr.Code(language="json", label="Reporte JSON")
                    report_btn.click(
                        fn=self.get_full_report,
                        outputs=report_output
                    )
            
            # Auto-refresh cada 10 segundos (opcional)
            gr.Markdown("---")
            gr.Markdown("💡 **Tip**: Usa los botones de actualización para ver las métricas más recientes")
        
        return interface
