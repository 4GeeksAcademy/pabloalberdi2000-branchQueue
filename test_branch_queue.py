"""Pruebas de control de calidad para BranchQueue."""

from __future__ import annotations

import io
import unittest
from collections import deque
from unittest.mock import patch

from branch_queue import BranchQueue, VALID_SERVICES, main_cli


class BranchQueueTests(unittest.TestCase):
	"""Valida comportamiento funcional y casos borde de BranchQueue."""

	def setUp(self) -> None:
		self.queue = BranchQueue()

	def test_internal_structure_per_service(self) -> None:
		self.assertEqual(set(self.queue._queues.keys()), set(VALID_SERVICES))
		for service in VALID_SERVICES:
			self.assertIsInstance(self.queue._queues[service], deque)

	def test_global_sequential_numbering_across_services(self) -> None:
		t1 = self.queue.issue_ticket("Ana", "deposito")
		t2 = self.queue.issue_ticket("Luis", "retiro")
		t3 = self.queue.issue_ticket("Marta", "gestion_cuenta")
		self.assertEqual([t1.number, t2.number, t3.number], [1, 2, 3])

	def test_fifo_is_preserved_per_service(self) -> None:
		self.queue.issue_ticket("Cliente 1", "deposito")
		self.queue.issue_ticket("Cliente 2", "deposito")
		self.queue.issue_ticket("Cliente 3", "deposito")

		first = self.queue.call_next("deposito")
		second = self.queue.call_next("deposito")
		third = self.queue.call_next("deposito")

		self.assertEqual(first.client_name, "Cliente 1")
		self.assertEqual(second.client_name, "Cliente 2")
		self.assertEqual(third.client_name, "Cliente 3")

	def test_required_operations_are_implemented(self) -> None:
		for method_name in (
			"issue_ticket",
			"call_next",
			"peek_next",
			"list_waiting",
			"stats",
		):
			self.assertTrue(hasattr(self.queue, method_name))

		self.queue.issue_ticket("Ana", "deposito")
		self.assertIsNotNone(self.queue.peek_next("deposito"))
		self.assertEqual(len(self.queue.list_waiting()["deposito"]), 1)
		self.assertEqual(self.queue.stats()["total"], 1)

	def test_safe_empty_queue_handling(self) -> None:
		self.assertIsNone(self.queue.peek_next("deposito"))
		with self.assertRaises(LookupError):
			self.queue.call_next("deposito")

	def test_invalid_service_is_rejected_without_increment(self) -> None:
		first = self.queue.issue_ticket("Ana", "deposito")
		self.assertEqual(first.number, 1)

		with self.assertRaises(ValueError):
			self.queue.issue_ticket("Pepe", "invalido")

		next_valid = self.queue.issue_ticket("Luis", "retiro")
		self.assertEqual(next_valid.number, 2)


class CLITests(unittest.TestCase):
	"""Valida que el CLI sea resiliente ante entradas invalidas."""

	def test_cli_loop_resilience(self) -> None:
		user_inputs = [
			"x",  # opcion invalida
			"1",
			"",  # nombre invalido
			"1",
			"Ana",
			"invalido",  # servicio invalido
			"2",
			"deposito",  # cola vacia
			"5",  # salida limpia
		]

		with patch("builtins.input", side_effect=user_inputs):
			with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
				main_cli()

		output = fake_out.getvalue()
		self.assertIn("Opción inválida", output)
		self.assertIn("no puede estar vacío", output)
		self.assertIn("Tipo de servicio inválido", output)
		self.assertIn("Cola vacía", output)
		self.assertIn("Saliendo del sistema", output)


if __name__ == "__main__":
	unittest.main()