<?php
class BilletsManager
{

  private $_db; // Instance de PDO.

  public function __construct($db)
  {
    $this->setDb($db);
  }

  public function add(Billet $billet)
  { 
    // Préparation de la requête d'insertion.
    // Assignation des valeurs pour le  id, image , titre, contenu auteur date de creation du Billet.
    // Exécution de la requête.
	  $q=$this->_db->prepare('INSERT INTO `billets`(`id`, `image`, `alt`, `titre`, `contenu`, `auteur`, `date_creation`) VALUES ([value-1],[value-2],[value-3],[value-4],[value-5],[value-6],[value-7]) ');
	 
	  
	  $q->bindValue(':id', $billet->id());
      $q->bindValue(':image', $billet->image(), PDO::PARAM_STR);
	  $q->bindValue(':alt', $billet->alt(), PDO::PARAM_STR);
	  $q->bindValue(':titre', $billet->titre(), PDO::PARAM_STR);
	  $q->bindValue(':contenu', $billet->contenu(), PDO::PARAM_STR);
	  $q->bindValue(':auteur', $billet->auteur(), PDO::PARAM_STR);
	  $q->bindValue(':date_creation', $billet->date_creation());
	  $q->execute();
		  
		  
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