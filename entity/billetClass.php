<?php
class Billet 
{
	protected 	$_id,
	  			$_image,
	  			$_alt,
	  			$_titre,
	  			$_contenu,
				$_auteur,
				$_date_creation,
				$_date_updated,
				$_is_publicated;
	
	
	private $_step;
// dans l'index
// $billet = new Billet($row);
	
public function __construct($row)
{
	$this->hydrate($row);
}
	
// Un tableau de données doit être passé à la fonction (d'où le préfixe « array »).
public function hydrate(array $data)
 {
	 foreach ($donnees as $key => $value)
	  {
		  
		  //$row['id'] = 5
		  
		  //$key = 'id'; $value = 5
		  // ->  setId  
	  
		  // is_publicated > setIs_publicated
		  
		    // On récupère le nom du setter correspondant à l'attribut.
		    $method = 'set'.ucfirst($key);
		    // Si le setter correspondant existe.
		    if (method_exists($this, $method))
		    {
		      // On appelle le setter.
		      $this->$method($value);
		    }
	  }
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
public function auteur()
{
	return $this->_auteur;
}
public function date_creation()
{
	return $this->_date_creation;
}
	public function date_updated ()
{
	return $this->_date_updated;
}
	public function is_publicated ()
{
	return $this->_is_publicated;
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
public function setImage($image)
  {
    if (is_string($image))
   
	{
		$this->_image = $image;	
	}
  }
public function setAlt($alt)
  {
    if (is_string($alt))
   
	{
		$this->_alt = $alt;	
	}
  }
public function setTitre($titre)
  {
    if (is_string($titre))
   
	{
		$this->_titre = $titre;	
	}
  }
public function setContenu($contenu)
  {
    if (is_string($contenu))
   
	{
		$this->_contenu = $contenu;	
	}
  }
public function setAuteur($auteur)
  {
    if (is_string($auteur))
   
	{
		$this->_auteur = $auteur;	
	}
  }
public function setDateCreation($date_creation)
  {
    if (is_string($date_creation))
   
	{
		$this->_date_creation = $date_creation;	
	}
  }
	
	public function setIs_publicated($value)
	{
		$this->is_publicated = $value;
	}
 }