<?php
class Billet 
{
	private $_id;
	private $_image;
	private $_alt;
	private $_titre;
	private $_contenu;
	private $_auteur;
	private $_date_creation;
		
}
// liste des getters

public function id()
{
	return $this->_id;
}

public function image()
{
	return $this->_image;
}

public function alt()
{
	return $this->_alt;
}

public function titre()
{
	return $this->_titre;
}

public function contenu()
{
	return $this->_contenu;
}
public function uteur()
{
	return $this->_uteur;
}

public function date_creation()
{
	return $this->_date_creation;
}

//Liste des setters

public function setId($id)
{
	 // On convertit l'argument en nombre entier.
    // Si c'en était déjà un, rien ne changera.
    // Sinon, la conversion donnera le nombre 0 (à quelques exceptions près, mais rien d'important ici).
    $id = (int) $id;
    
    // On vérifie ensuite si ce nombre est bien strictement positif.
    if ($id > 0)
    {
      // Si c'est le cas, c'est tout bon, on assigne la valeur à l'attribut correspondant.
      $this->_id = $id;
    }
}