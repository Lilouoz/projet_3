<?php
class BilletsManager
{
	private $_db;
{
  private $_db; // Instance de PDO.

  public function __construct($db)
  {
    $this->setDb($db);
  }

  public function add(Billet $billet)
  {
    // Préparation de la requête d'insertion.
    // Assignation des valeurs pour le nom, contenu et du Billet.
    // Exécution de la requête.
  }

  public function delete(Billet $billet)
  {
    // Exécute une requête de type DELETE.
  }

  public function get($id)
  {
    // Exécute une requête de type SELECT avec une clause WHERE, et retourne un objet Billet.
  }

  public function getList()
  {
    // Retourne la liste de tous les Billets.
  }

  public function update(Billet $billet)
  {
    // Prépare une requête de type UPDATE.
    // Assignation des valeurs à la requête.
    // Exécution de la requête.
  }

  public function setDb(PDO $db)
  {
    $this->_db = $db;
  }
}