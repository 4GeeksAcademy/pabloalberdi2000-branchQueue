"""Sistema de gestión de turnos para una sucursal bancaria.

Este módulo define un modelo de ticket y un gestor de colas por tipo de
servicio con numeración global secuencial.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Dict, Final, List, Literal, Optional, cast


ServiceType = Literal["deposito", "retiro", "gestion_cuenta"]
VALID_SERVICES: Final[tuple[str, ...]] = ("deposito", "retiro", "gestion_cuenta")


@dataclass(frozen=True)
class Ticket:
	"""Representa un ticket de atención emitido para un cliente.

	Attributes:
		number: Número secuencial global del ticket.
		client_name: Nombre del cliente.
		service_type: Tipo de servicio solicitado.
		issued_at: Fecha y hora exacta de emisión.
	"""

	number: int
	client_name: str
	service_type: ServiceType
	issued_at: datetime


class BranchQueue:
	"""Gestiona colas independientes por servicio con numeración global.

	Cada servicio mantiene su propia cola FIFO y todos los tickets comparten
	el mismo contador secuencial global.
	"""

	def __init__(self) -> None:
		self._next_ticket_number: int = 1
		self._queues: Dict[ServiceType, Deque[Ticket]] = {
			"deposito": deque(),
			"retiro": deque(),
			"gestion_cuenta": deque(),
		}

	def _validate_service_type(self, service_type: str) -> ServiceType:
		"""Valida y devuelve el tipo de servicio como `ServiceType`."""
		if service_type not in VALID_SERVICES:
			raise ValueError(
				f"Tipo de servicio inválido: {service_type!r}. "
				f"Servicios permitidos: {', '.join(VALID_SERVICES)}"
			)
		return cast(ServiceType, service_type)

	def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
		"""Emite un ticket y lo agrega a la cola del servicio indicado.

		Args:
			client_name: Nombre del cliente.
			service_type: Tipo de servicio solicitado.

		Returns:
			El ticket emitido.
		"""
		normalized_service = self._validate_service_type(service_type)
		ticket = Ticket(
			number=self._next_ticket_number,
			client_name=client_name,
			service_type=normalized_service,
			issued_at=datetime.now(),
		)
		self._queues[normalized_service].append(ticket)
		self._next_ticket_number += 1
		return ticket

	def call_next(self, service_type: str) -> Ticket:
		"""Desencola y devuelve el siguiente ticket del servicio indicado.

		Raises:
			ValueError: Si el tipo de servicio es inválido.
			LookupError: Si no hay clientes esperando en ese servicio.
		"""
		normalized_service = self._validate_service_type(service_type)
		queue = self._queues[normalized_service]
		if not queue:
			raise LookupError(
				f"No hay clientes en espera para el servicio '{normalized_service}'."
			)
		return queue.popleft()

	def peek_next(self, service_type: str) -> Optional[Ticket]:
		"""Obtiene el siguiente ticket en espera sin retirarlo de la cola.

		Retorna `None` si el servicio es inválido o no tiene clientes en espera.
		"""
		if service_type not in VALID_SERVICES:
			return None

		normalized_service = cast(ServiceType, service_type)
		queue = self._queues[normalized_service]
		if not queue:
			return None
		return queue[0]

	def list_waiting(self) -> Dict[str, List[Ticket]]:
		"""Lista los tickets en espera por servicio en orden FIFO."""
		return {service: list(queue) for service, queue in self._queues.items()}

	def stats(self) -> Dict[str, int]:
		"""Retorna el conteo de clientes en espera por servicio y total."""
		counts: Dict[str, int] = {
			service: len(queue) for service, queue in self._queues.items()
		}
		counts["total"] = sum(counts.values())
		return counts


def _prompt_service_type() -> str:
	"""Solicita y normaliza el tipo de servicio ingresado por el usuario."""
	print(f"Servicios válidos: {', '.join(VALID_SERVICES)}")
	return input("Ingrese tipo de servicio: ").strip().lower()


def _print_waiting_list(waiting: Dict[str, List[Ticket]]) -> None:
	"""Imprime la lista de espera agrupada por tipo de servicio."""
	print("\nLista de espera actual:")
	for service in VALID_SERVICES:
		tickets = waiting[service]
		print(f"- {service} ({len(tickets)}):")
		if not tickets:
			print("  Sin clientes en espera.")
			continue
		for ticket in tickets:
			print(
				"  "
				f"Ticket #{ticket.number} | "
				f"Cliente: {ticket.client_name} | "
				f"Emitido: {ticket.issued_at:%Y-%m-%d %H:%M:%S}"
			)


def main_cli() -> None:
	"""Ejecuta una interfaz de consola interactiva para gestionar la sucursal."""
	queue = BranchQueue()

	while True:
		print("\n=== Sistema BranchQueue ===")
		print("1. Emitir un nuevo ticket")
		print("2. Llamar al siguiente cliente")
		print("3. Ver la lista de espera completa")
		print("4. Ver estadísticas de la cola")
		print("5. Salir")

		option = input("Seleccione una opción (1-5): ").strip()

		if option == "1":
			try:
				client_name = input("Ingrese nombre del cliente: ").strip()
				if not client_name:
					print("Error: el nombre del cliente no puede estar vacío.")
					continue

				service_type = _prompt_service_type()
				ticket = queue.issue_ticket(client_name, service_type)
				print(
					f"Ticket emitido correctamente: #{ticket.number} "
					f"para servicio '{ticket.service_type}'."
				)
			except ValueError as error:
				print(f"Error al emitir ticket: {error}")

		elif option == "2":
			try:
				service_type = _prompt_service_type()
				next_ticket = queue.call_next(service_type)
				print(
					"Siguiente cliente a atender: "
					f"Ticket #{next_ticket.number} - {next_ticket.client_name}"
				)
			except ValueError as error:
				print(f"Error de validación: {error}")
			except LookupError as error:
				print(f"Cola vacía: {error}")

		elif option == "3":
			waiting = queue.list_waiting()
			_print_waiting_list(waiting)

		elif option == "4":
			stats = queue.stats()
			print("\nEstadísticas de la cola:")
			for service in VALID_SERVICES:
				print(f"- {service}: {stats[service]}")
			print(f"- total: {stats['total']}")

		elif option == "5":
			print("Saliendo del sistema. Hasta luego.")
			break

		else:
			print("Opción inválida. Ingrese un número entre 1 y 5.")


if __name__ == "__main__":
	main_cli()
