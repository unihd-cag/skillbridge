.. _overview:

Overview
========

What Is this?
-------------


The Python-Skill Bridge is a set of tools that allows you to control Virtuoso via
its Skill console remotely from python. It consists of several parts:

- A Skill script that must be executed inside the Skill console. This script will start and manage the python server
- A python server that waits for Skill commands, runs them and sends the result back.
- A python client library that encapsulates the connection and transport details and offers a pythonic interface to the Skill code.

.. image:: /images/components.svg
